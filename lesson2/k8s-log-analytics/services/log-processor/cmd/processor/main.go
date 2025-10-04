package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var (
	processedLogsCount = 0
)

type LogProcessor struct {
}

type LogEntry struct {
	Timestamp string                 `json:"timestamp"`
	Level     string                 `json:"level"`
	Service   string                 `json:"service"`
	Message   string                 `json:"message"`
	Metadata  map[string]interface{} `json:"metadata"`
}

func NewLogProcessor() (*LogProcessor, error) {
	log.Println("Creating log processor...")
	return &LogProcessor{}, nil
}

func (lp *LogProcessor) ProcessLog(ctx context.Context, logKey string) error {
	log.Printf("Processing log: %s", logKey)
	processedLogsCount++
	return nil
}

func (lp *LogProcessor) Start(ctx context.Context) error {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("Shutting down processor")
			return nil
		case <-ticker.C:
			// Simulate processing logs
			log.Printf("Processing logs... (processed: %d)", processedLogsCount)
			lp.ProcessLog(ctx, "simulated-log")
		}
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "healthy")
}

func readyHandler(lp *LogProcessor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "ready")
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func main() {
	processor, err := NewLogProcessor()
	if err != nil {
		log.Fatalf("Failed to create processor: %v", err)
	}

	// Setup HTTP server for health checks and metrics
	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/ready", readyHandler(processor))
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "# HELP logs_processed_total Total number of logs processed\n")
		fmt.Fprintf(w, "# TYPE logs_processed_total counter\n")
		fmt.Fprintf(w, "logs_processed_total %d\n", processedLogsCount)
	})

	server := &http.Server{
		Addr:    ":9000",
		Handler: mux,
	}

	// Start HTTP server
	go func() {
		log.Println("Starting HTTP server on :9000")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	// Start log processor
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		if err := processor.Start(ctx); err != nil {
			log.Printf("Processor error: %v", err)
		}
	}()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Received shutdown signal")
	cancel()

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Printf("Server shutdown error: %v", err)
	}

	log.Println("Shutdown complete")
}

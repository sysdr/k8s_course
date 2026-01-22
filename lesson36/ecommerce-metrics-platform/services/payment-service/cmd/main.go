package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	paymentsProcessed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "payments_processed_total",
			Help: "Total number of payments processed",
		},
		[]string{"status", "method", "processor"},
	)

	paymentDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "payment_processing_duration_seconds",
			Help:    "Payment processing duration in seconds",
			Buckets: []float64{0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0},
		},
		[]string{"method", "processor"},
	)

	paymentAmount = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "payment_amount_dollars",
			Help:    "Payment amount distribution",
			Buckets: []float64{10, 50, 100, 500, 1000, 5000, 10000},
		},
		[]string{"method"},
	)

	fraudDetectionScore = prometheus.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "fraud_detection_score",
			Help:    "Fraud detection score distribution",
			Buckets: prometheus.LinearBuckets(0, 10, 11),
		},
	)

	activePayments = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "active_payments_current",
			Help: "Number of currently processing payments",
		},
	)
)

func init() {
	prometheus.MustRegister(paymentsProcessed)
	prometheus.MustRegister(paymentDuration)
	prometheus.MustRegister(paymentAmount)
	prometheus.MustRegister(fraudDetectionScore)
	prometheus.MustRegister(activePayments)
}

type PaymentRequest struct {
	OrderID       string  `json:"order_id"`
	Amount        float64 `json:"amount"`
	Currency      string  `json:"currency"`
	Method        string  `json:"method"`
	CustomerID    string  `json:"customer_id"`
}

type PaymentResponse struct {
	TransactionID string  `json:"transaction_id"`
	Status        string  `json:"status"`
	ProcessedAt   string  `json:"processed_at"`
	FraudScore    float64 `json:"fraud_score"`
	ProcessorUsed string  `json:"processor_used"`
}

func processPayment(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	activePayments.Inc()
	defer activePayments.Dec()

	var req PaymentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Simulate payment processor selection
	processors := []string{"stripe", "braintree", "adyen"}
	processor := processors[rand.Intn(len(processors))]

	// Simulate fraud detection
	fraudScore := rand.Float64() * 100
	fraudDetectionScore.Observe(fraudScore)

	// Simulate processing time based on method
	var processingTime time.Duration
	switch req.Method {
	case "credit_card":
		processingTime = time.Duration(50+rand.Intn(200)) * time.Millisecond
	case "debit_card":
		processingTime = time.Duration(30+rand.Intn(150)) * time.Millisecond
	case "paypal":
		processingTime = time.Duration(100+rand.Intn(300)) * time.Millisecond
	default:
		processingTime = time.Duration(100+rand.Intn(200)) * time.Millisecond
	}

	time.Sleep(processingTime)

	// Determine status (95% success rate)
	status := "approved"
	if rand.Float64() < 0.05 || fraudScore > 80 {
		status = "declined"
	}

	// Record metrics
	paymentsProcessed.WithLabelValues(status, req.Method, processor).Inc()
	paymentDuration.WithLabelValues(req.Method, processor).Observe(time.Since(start).Seconds())
	paymentAmount.WithLabelValues(req.Method).Observe(req.Amount)

	response := PaymentResponse{
		TransactionID: fmt.Sprintf("TXN-%d-%d", time.Now().Unix(), rand.Intn(9999)),
		Status:        status,
		ProcessedAt:   time.Now().UTC().Format(time.RFC3339),
		FraudScore:    fraudScore,
		ProcessorUsed: processor,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"service":   "payment-service",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	})
}

func readinessCheck(w http.ResponseWriter, r *http.Request) {
	// Check if we can process payments
	if activePayments.Get() > 100 {
		http.Error(w, "Service overloaded", http.StatusServiceUnavailable)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

func main() {
	rand.Seed(time.Now().UnixNano())

	http.HandleFunc("/api/payments", processPayment)
	http.HandleFunc("/health", healthCheck)
	http.HandleFunc("/ready", readinessCheck)
	http.Handle("/metrics", promhttp.Handler())

	log.Println("Payment Service starting on :8001")
	if err := http.ListenAndServe(":8001", nil); err != nil {
		log.Fatal(err)
	}
}

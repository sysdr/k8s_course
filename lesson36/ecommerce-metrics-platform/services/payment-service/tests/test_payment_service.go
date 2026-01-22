package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

const baseURL = "http://localhost:8001"

func TestHealthCheck(t *testing.T) {
	resp, err := http.Get(baseURL + "/health")
	if err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if result["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got '%v'", result["status"])
	}
}

func TestReadinessCheck(t *testing.T) {
	resp, err := http.Get(baseURL + "/ready")
	if err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}
}

func TestMetricsEndpoint(t *testing.T) {
	resp, err := http.Get(baseURL + "/metrics")
	if err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check for Prometheus metrics
	buf := new(bytes.Buffer)
	buf.ReadFrom(resp.Body)
	body := buf.String()

	if !contains(body, "payments_processed_total") {
		t.Error("Metrics should contain 'payments_processed_total'")
	}
}

func TestProcessPayment(t *testing.T) {
	paymentReq := PaymentRequest{
		OrderID:    "ORD-123",
		Amount:     99.99,
		Currency:   "USD",
		Method:     "credit_card",
		CustomerID: "CUST-456",
	}

	jsonData, err := json.Marshal(paymentReq)
	if err != nil {
		t.Fatalf("Failed to marshal request: %v", err)
	}

	resp, err := http.Post(baseURL+"/api/payments", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		t.Fatalf("Failed to send request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var result PaymentResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if result.TransactionID == "" {
		t.Error("TransactionID should not be empty")
	}

	if result.Status != "approved" && result.Status != "declined" {
		t.Errorf("Expected status 'approved' or 'declined', got '%s'", result.Status)
	}
}

func TestMetricsAfterPayment(t *testing.T) {
	// Get initial metrics
	initialResp, err := http.Get(baseURL + "/metrics")
	if err != nil {
		t.Fatalf("Failed to get initial metrics: %v", err)
	}
	initialBuf := new(bytes.Buffer)
	initialBuf.ReadFrom(initialResp)
	initialMetrics := initialBuf.String()
	initialResp.Body.Close()

	// Process a payment
	paymentReq := PaymentRequest{
		OrderID:    "METRICS-TEST",
		Amount:     50.00,
		Currency:   "USD",
		Method:     "debit_card",
		CustomerID: "TEST-CUST",
	}

	jsonData, _ := json.Marshal(paymentReq)
	http.Post(baseURL+"/api/payments", "application/json", bytes.NewBuffer(jsonData))

	// Wait for metrics to update
	time.Sleep(500 * time.Millisecond)

	// Get updated metrics
	updatedResp, err := http.Get(baseURL + "/metrics")
	if err != nil {
		t.Fatalf("Failed to get updated metrics: %v", err)
	}
	updatedBuf := new(bytes.Buffer)
	updatedBuf.ReadFrom(updatedResp)
	updatedMetrics := updatedBuf.String()
	updatedResp.Body.Close()

	// Metrics should have changed
	if updatedMetrics == initialMetrics {
		t.Error("Metrics should have changed after processing payment")
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && 
		(s[:len(substr)] == substr || s[len(s)-len(substr):] == substr || 
		containsSubstring(s, substr)))
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

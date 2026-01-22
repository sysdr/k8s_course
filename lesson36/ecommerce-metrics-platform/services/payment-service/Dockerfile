FROM golang:1.21-alpine as builder

WORKDIR /build
COPY go.mod ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o payment-service ./cmd

FROM alpine:3.18

RUN apk --no-cache add ca-certificates
RUN adduser -D -u 1000 appuser

WORKDIR /app
COPY --from=builder /build/payment-service .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

CMD ["./payment-service"]

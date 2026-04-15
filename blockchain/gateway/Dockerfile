FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway-service .

FROM alpine:latest
WORKDIR /app

# Copier le binaire gateway compilé
COPY --from=builder /app/gateway-service .

# Les volumes seront montés :
# /crypto-material → certificats Fabric
# /fabric-config   → core.yaml
# /fabric-bin      → binaire peer

EXPOSE 9999
CMD ["./gateway-service"]

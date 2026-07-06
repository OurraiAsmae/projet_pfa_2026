FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway-service .

FROM alpine:latest
WORKDIR /app

# Compatibilité glibc : le binaire peer de fabric-samples est compilé avec glibc
# (nécessite libresolv.so.2 etc.) ; gcompat + libresolv fournissent la couche de
# compatibilité sous Alpine/musl.
RUN apk add --no-cache gcompat libc6-compat

# Copier le binaire gateway compilé
COPY --from=builder /app/gateway-service .

# Les volumes seront montés :
# /crypto-material → certificats Fabric
# /fabric-config   → core.yaml
# /fabric-bin      → binaire peer

EXPOSE 9999
CMD ["./gateway-service"]

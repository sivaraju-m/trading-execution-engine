# Multi-stage Docker build for Trading Execution Engine
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Add metadata
LABEL maintainer="AI Trading Machine Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.version=$VERSION \
      org.label-schema.name="trading-execution-engine" \
      org.label-schema.description="SEBI-compliant trading execution engine for production deployment"

# Install system dependencies and TA-Lib C library
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    ca-certificates \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install TA-Lib C library with architecture support
RUN cd /tmp && \
    wget https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    # Update config.sub and config.guess for modern architecture support \
    wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' && \
    wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' && \
    chmod +x config.sub config.guess && \
    ./configure --prefix=/usr/local --build=$(./config.guess) && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/ta-lib* && \
    ldconfig

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Set environment variables for TA-Lib
ENV TA_LIBRARY_PATH=/usr/local/lib
ENV TA_INCLUDE_PATH=/usr/local/include
ENV LDFLAGS="-L/usr/local/lib"
ENV CPPFLAGS="-I/usr/local/include"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash trader && \
    mkdir -p /app/logs /app/data && \
    chown -R trader:trader /app

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy TA-Lib libraries from builder
COPY --from=builder /usr/local/lib/libta_lib* /usr/local/lib/
COPY --from=builder /usr/local/include/ta-lib /usr/local/include/ta-lib

# Run ldconfig to update library cache
RUN ldconfig

# Copy application code
COPY --from=builder /app /app

# Set ownership to non-root user
RUN chown -R trader:trader /app

# Switch to non-root user
USER trader

# Health check for SEBI compliance monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import trading_execution_engine; print('Service healthy')" || exit 1

# Environment variables for production
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    SEBI_COMPLIANCE=enabled \
    PAPER_TRADING=true

# Expose port for health checks and API
EXPOSE 8080

# Default command for production (SEBI-compliant paper trading)
CMD ["python", "-m", "trading_execution_engine.main"]

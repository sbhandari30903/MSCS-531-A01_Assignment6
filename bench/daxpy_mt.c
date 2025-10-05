#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    float *x; float *y; float a; size_t start; size_t end;
} daxpy_args_t;

static void *worker(void *arg) {
    daxpy_args_t *ctx = (daxpy_args_t*)arg;
    for (size_t i = ctx->start; i < ctx->end; i++) {
        ctx->y[i] = ctx->a * ctx->x[i] + ctx->y[i];
    }
    return NULL;
}

static double now_seconds() {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    size_t N = 10*1000*1000; // default 10M elements
    int T = 4;               // default threads
    float a = 2.0f;
    if (argc > 1) N = strtoull(argv[1], NULL, 10);
    if (argc > 2) T = atoi(argv[2]);

    float *x = aligned_alloc(64, N * sizeof(float));
    float *y = aligned_alloc(64, N * sizeof(float));
    if (!x || !y) { perror("alloc"); return 1; }
    for (size_t i=0;i<N;i++) { x[i] = (float)(i % 100) * 0.5f; y[i] = 1.0f; }

    pthread_t *ths = malloc(T * sizeof(pthread_t));
    daxpy_args_t *args = malloc(T * sizeof(daxpy_args_t));

    double t0 = now_seconds();
    size_t chunk = (N + T - 1) / T;
    for (int t=0; t<T; t++) {
        size_t s = t * chunk;
        size_t e = s + chunk; if (e > N) e = N;
        args[t] = (daxpy_args_t){ .x=x, .y=y, .a=a, .start=s, .end=e };
        pthread_create(&ths[t], NULL, worker, &args[t]);
    }
    for (int t=0; t<T; t++) pthread_join(ths[t], NULL);
    double t1 = now_seconds();

    // checksum to keep compiler honest
    double sum = 0.0; for (size_t i=0;i<N;i++) sum += y[i];
    printf("N=%zu T=%d time=%.6f sec checksum=%.3f\n", N, T, (t1-t0), sum);

    free(ths); free(args); free(x); free(y);
    return 0;
}

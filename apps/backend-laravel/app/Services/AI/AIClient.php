<?php

namespace App\Services\AI;

use Illuminate\Support\Facades\Http;

class AIClient
{
    public function __construct(private readonly SignatureService $signatureService)
    {
    }

    public function chat(array $payload): array
    {
        return $this->post('/ai/chat', $payload);
    }

    public function analyze(array $payload): array
    {
        return $this->post('/ai/analyze', $payload);
    }

    public function classify(array $payload): array
    {
        return $this->post('/ai/classify', $payload);
    }

    private function post(string $path, array $payload): array
    {
        $body = json_encode($payload, JSON_UNESCAPED_UNICODE);
        $timestamp = time();
        $secret = (string) config('ai.internal_secret');
        $signature = $this->signatureService->buildSignature($body, $timestamp, $secret);

        $response = Http::timeout((int) config('ai.timeout_seconds', 20))
            ->acceptJson()
            ->withHeaders([
                'X-Request-Timestamp' => (string) $timestamp,
                'X-Internal-Signature' => $signature,
                'X-Internal-Key' => (string) config('ai.internal_key'),
            ])
            ->post(rtrim((string) config('ai.base_url'), '/') . $path, $payload);

        $response->throw();
        return $response->json();
    }
}

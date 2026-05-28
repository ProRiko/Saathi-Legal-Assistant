<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class VerifyServiceSignature
{
    public function handle(Request $request, Closure $next)
    {
        $key = (string) $request->header('X-Internal-Key', '');
        $timestamp = (string) $request->header('X-Request-Timestamp', '');
        $signature = (string) $request->header('X-Internal-Signature', '');

        $expectedKey = (string) config('ai.internal_key');
        $secret = (string) config('ai.internal_secret');

        if ($key !== $expectedKey || !$timestamp || !$signature || !$secret) {
            return response()->json(['status' => 'error', 'message' => 'Invalid internal signature'], 401);
        }

        $payload = $request->getContent();
        $expected = hash_hmac('sha256', $timestamp . '.' . $payload, $secret);

        if (!hash_equals($expected, $signature)) {
            return response()->json(['status' => 'error', 'message' => 'Signature mismatch'], 401);
        }

        return $next($request);
    }
}

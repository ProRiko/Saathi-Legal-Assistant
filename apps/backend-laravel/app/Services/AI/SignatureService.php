<?php

namespace App\Services\AI;

class SignatureService
{
    public function buildSignature(string $body, int $timestamp, string $secret): string
    {
        return hash_hmac('sha256', $timestamp . '.' . $body, $secret);
    }
}

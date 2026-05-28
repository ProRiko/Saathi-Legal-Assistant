<?php

return [
    'base_url' => env('AI_SERVICE_BASE_URL', 'http://ai-python:8081'),
    'timeout_seconds' => env('AI_SERVICE_TIMEOUT_SECONDS', 20),
    'internal_key' => env('AI_SERVICE_INTERNAL_KEY', ''),
    'internal_secret' => env('AI_SERVICE_INTERNAL_SECRET', ''),
];

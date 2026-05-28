<?php

return [
    'chat_per_minute' => env('CHAT_RATE_LIMIT_PER_MINUTE', 30),
    'documents_per_minute' => env('DOCUMENT_RATE_LIMIT_PER_MINUTE', 10),
];

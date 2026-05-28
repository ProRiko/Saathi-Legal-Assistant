<?php

namespace App\Services\Template;

class TemplateRenderer
{
    public function render(string $body, array $fields): string
    {
        $rendered = $body;

        foreach ($fields as $key => $value) {
            $token = '[' . $key . ']';
            $rendered = str_replace($token, (string) $value, $rendered);
        }

        return trim($rendered);
    }
}

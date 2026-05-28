<?php

namespace App\Services\Template;

use Illuminate\Support\Facades\Storage;

class PdfService
{
    public function generateAndStore(string $title, string $renderedText, string $filename): string
    {
        // Replace this plain-text write with DomPDF/Snappy implementation in production.
        $path = 'generated-documents/' . $filename;
        Storage::disk('local')->put($path, "TITLE: {$title}\n\n{$renderedText}");
        return $path;
    }
}

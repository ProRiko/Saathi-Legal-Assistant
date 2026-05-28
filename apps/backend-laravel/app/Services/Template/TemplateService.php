<?php

namespace App\Services\Template;

use App\Models\User;
use App\Models\Template;
use App\Models\GeneratedDocument;
use Illuminate\Support\Str;
use Illuminate\Support\Carbon;

class TemplateService
{
    public function __construct(
        private readonly TemplateRenderer $renderer,
        private readonly PdfService $pdfService,
    ) {
    }

    public function generate(User $user, array $data): array
    {
        $template = Template::query()
            ->where('slug', $data['template_slug'])
            ->where('is_active', true)
            ->firstOrFail();

        $rendered = $this->renderer->render($template->body, $data['fields']);
        $title = $data['title'] ?? $template->title;
        $documentId = (string) Str::uuid();
        $filePath = $this->pdfService->generateAndStore($title, $rendered, $documentId . '.pdf');

        GeneratedDocument::create([
            'id' => $documentId,
            'user_id' => $user->id,
            'template_id' => $template->id,
            'conversation_id' => $data['conversation_id'] ?? null,
            'title' => $title,
            'fields' => $data['fields'],
            'rendered_text' => $rendered,
            'file_path' => $filePath,
            'mime_type' => 'application/pdf',
            'created_at' => Carbon::now(),
        ]);

        return [
            'document_id' => $documentId,
            'title' => $title,
            'file_path' => $filePath,
            'status' => 'success',
        ];
    }
}

<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class TemplateGenerateRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'template_slug' => ['required', 'string', 'max:120'],
            'fields' => ['required', 'array'],
            'conversation_id' => ['nullable', 'uuid'],
            'title' => ['nullable', 'string', 'max:255'],
        ];
    }
}

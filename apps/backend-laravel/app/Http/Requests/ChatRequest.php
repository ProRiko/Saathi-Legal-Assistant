<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class ChatRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'conversation_id' => ['nullable', 'uuid'],
            'message' => ['required', 'string', 'min:1', 'max:4000'],
            'language' => ['nullable', 'string', 'max:32'],
        ];
    }
}

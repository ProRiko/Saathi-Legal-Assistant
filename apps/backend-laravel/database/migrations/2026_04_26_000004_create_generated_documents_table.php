<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('generated_documents', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignId('user_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('template_id')->constrained('templates');
            $table->uuid('conversation_id')->nullable();
            $table->foreign('conversation_id')->references('id')->on('conversations')->nullOnDelete();
            $table->string('title');
            $table->json('fields');
            $table->longText('rendered_text');
            $table->string('file_path');
            $table->string('mime_type', 120)->default('application/pdf');
            $table->timestamp('created_at')->useCurrent();

            $table->index(['user_id', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('generated_documents');
    }
};

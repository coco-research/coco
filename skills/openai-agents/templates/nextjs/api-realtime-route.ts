/**
 * Next.js API Route for Realtime Voice Agent
 *
 * File: app/api/voice/session/route.ts
 *
 * Demonstrates:
 * - Generating ephemeral API keys for voice sessions
 * - Securing realtime agent access
 * - NEVER exposing main API key to clients
 *
 * CRITICAL: Never send your main OPENAI_API_KEY to the browser!
 * Use ephemeral session keys with short expiration.
 */

import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

// ========================================
// POST /api/voice/session
// Generate ephemeral API key for voice session
// ========================================

export async function POST(request: NextRequest) {
  try {
    // Optional: Authenticate user first
    // const session = await getServerSession(authOptions);
    // if (!session) {
    //   return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // }

    // Create OpenAI client with main API key (server-side only)
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });

    // Generate ephemeral key
    // NOTE: As of 2025-10-26, OpenAI doesn't have a dedicated ephemeral key endpoint
    // You may need to use session tokens or implement your own proxy
    //
    // Recommended approach: Create a proxy that validates requests and
    // forwards to OpenAI API with your key server-side

    // For demonstration, we'll show the pattern:
    // In production, implement a secure proxy or use OpenAI's ephemeral keys when available

    // Option 1: Return a session token (your own implementation)
    const sessionToken = generateSecureSessionToken();

    // Store session token mapping to your API key in Redis/KV
    // await redis.set(`session:${sessionToken}`, process.env.OPENAI_API_KEY, {
    //   ex: 3600, // 1 hour expiration
    // });

    return NextResponse.json({
      sessionToken,
      expiresIn: 3600, // seconds
    });

    // Option 2: If OpenAI provides ephemeral keys API (future)
    // const ephemeralKey = await openai.ephemeralKeys.create({
    //   expiresIn: 3600,
    // });
    // return NextResponse.json({
    //   apiKey: ephemeralKey.key,
    //   expiresIn: ephemeralKey.expiresIn,
    // });

  } catch (error: any) {
    console.error('Session creation error:', error);

    return NextResponse.json(
      { error: 'Failed to create session' },
      { status: 500 }
    );
  }
}

// ========================================
// Helper: Generate Secure Session Token
// ========================================

function generateSecureSessionToken(): string {
  // Generate cryptographically secure random token
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// ========================================
// Proxy Endpoint (Recommended Pattern)
// File: app/api/voice/proxy/route.ts
// ========================================

/**
 * This proxy validates session tokens and forwards requests to OpenAI API
 * This is the RECOMMENDED approach to avoid exposing your API key
 */

export async function POST_PROXY(request: NextRequest) {
  try {
    // Get session token from request
    const authHeader = request.headers.get('authorization');
    const sessionToken = authHeader?.replace('Bearer ', '');

    if (!sessionToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Validate session token
    // const apiKey = await redis.get(`session:${sessionToken}`);
    // if (!apiKey) {
    //   return NextResponse.json({ error: 'Invalid session' }, { status: 401 });
    // }

    // Get the actual OpenAI API request from client
    const body = await request.json();

    // Forward to OpenAI API with server-side key
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });

    // Forward request to OpenAI Realtime API
    // Implementation depends on the exact endpoint being called
    // This is a simplified example

    return NextResponse.json({
      message: 'Proxy implementation needed',
    });

  } catch (error: any) {
    return NextResponse.json(
      { error: 'Proxy error' },
      { status: 500 }
    );
  }
}

// ========================================
// Important Security Notes
// ========================================

/**
 * SECURITY CHECKLIST:
 *
 * 1. ✅ NEVER send OPENAI_API_KEY to browser
 * 2. ✅ Use ephemeral/session tokens with expiration
 * 3. ✅ Implement rate limiting per user/session
 * 4. ✅ Authenticate users before generating tokens
 * 5. ✅ Store session tokens in secure storage (Redis/KV)
 * 6. ✅ Log all voice session creation for monitoring
 * 7. ✅ Set maximum session duration (e.g., 1 hour)
 * 8. ✅ Implement cost controls and usage tracking
 *
 * RECOMMENDED ARCHITECTURE:
 *
 * Browser Client → Next.js Proxy → OpenAI API
 *     ↓
 * Session Token (never sees main API key)
 *
 * Alternative: Use OpenAI's official ephemeral key endpoint when available
 */

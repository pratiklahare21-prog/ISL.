import { Request, Response } from "express";
import { eq, and, desc } from "drizzle-orm";
import { db } from "../db/client";
import { translationSessions } from "../db/schema";
import { ApiError } from "../utils/ApiError";
import type { CreateSessionInput, FinalizeSessionInput } from "@isl/shared";

export async function createSession(req: Request, res: Response) {
  const { title } = req.body as CreateSessionInput;
  const userId = req.user!.userId;

  const [created] = await db
    .insert(translationSessions)
    .values({ userId, title: title ?? null })
    .returning();

  return res.status(201).json({ success: true, data: created });
}

export async function finalizeSession(req: Request, res: Response) {
  const userId = req.user!.userId;
  const { id } = req.params;
  const { transcript, durationMs } = req.body as FinalizeSessionInput;

  const existing = await db.query.translationSessions.findFirst({
    where: and(
      eq(translationSessions.id, id),
      eq(translationSessions.userId, userId)
    ),
  });
  if (!existing) throw ApiError.notFound("Session not found");

  const avgConfidence =
    transcript.length > 0
      ? transcript.reduce((sum, t) => sum + t.confidence, 0) / transcript.length
      : null;

  const [updated] = await db
    .update(translationSessions)
    .set({
      transcript,
      durationMs,
      signCount: transcript.length,
      avgConfidence,
    })
    .where(eq(translationSessions.id, id))
    .returning();

  return res.json({ success: true, data: updated });
}

export async function listSessions(req: Request, res: Response) {
  const userId = req.user!.userId;
  const sessions = await db.query.translationSessions.findMany({
    where: eq(translationSessions.userId, userId),
    orderBy: desc(translationSessions.createdAt),
    limit: 50,
  });
  return res.json({ success: true, data: sessions });
}

export async function getSession(req: Request, res: Response) {
  const userId = req.user!.userId;
  const { id } = req.params;
  const session = await db.query.translationSessions.findFirst({
    where: and(
      eq(translationSessions.id, id),
      eq(translationSessions.userId, userId)
    ),
  });
  if (!session) throw ApiError.notFound("Session not found");
  return res.json({ success: true, data: session });
}

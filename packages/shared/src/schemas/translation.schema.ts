import { z } from "zod";

/**
 * A single (x, y, z) landmark point normalized by MediaPipe (0-1 range,
 * z is relative depth). We keep this generic so it covers hand landmarks
 * (21 points/hand) and pose landmarks (33 points) alike.
 */
export const landmarkPointSchema = z.object({
  x: z.number(),
  y: z.number(),
  z: z.number().optional().default(0),
});

export type LandmarkPoint = z.infer<typeof landmarkPointSchema>;

/**
 * The full landmark payload extracted from a single video frame.
 * left_hand / right_hand are null when that hand is not visible.
 * pose is optional — only included if pose-based signs are enabled.
 */
export const frameLandmarksSchema = z.object({
  frameIndex: z.number().int().nonnegative(),
  timestampMs: z.number(),
  leftHand: z.array(landmarkPointSchema).length(21).nullable(),
  rightHand: z.array(landmarkPointSchema).length(21).nullable(),
  pose: z.array(landmarkPointSchema).length(33).nullable().optional(),
});

export type FrameLandmarks = z.infer<typeof frameLandmarksSchema>;

/**
 * Client -> ml-service websocket message: a raw video frame (base64 JPEG)
 * to be processed. Keeping the raw-frame extraction server-side (Python/
 * MediaPipe) means the browser doesn't need a WASM MediaPipe build.
 */
export const wsFrameMessageSchema = z.object({
  type: z.literal("frame"),
  sessionId: z.string(),
  data: z.string(), // base64-encoded JPEG
  timestampMs: z.number(),
});

export type WsFrameMessage = z.infer<typeof wsFrameMessageSchema>;

export const wsControlMessageSchema = z.object({
  type: z.enum(["start", "stop", "reset"]),
  sessionId: z.string(),
});

export type WsControlMessage = z.infer<typeof wsControlMessageSchema>;

export const wsClientMessageSchema = z.union([
  wsFrameMessageSchema,
  wsControlMessageSchema,
]);

export type WsClientMessage = z.infer<typeof wsClientMessageSchema>;

/**
 * ml-service -> client websocket message: a prediction result.
 * `stable` is true only once the prediction has been confirmed across
 * several consecutive windows (this is what should actually be spoken/
 * appended to the transcript, to avoid flickering/false triggers).
 */
export const wsPredictionMessageSchema = z.object({
  type: z.literal("prediction"),
  sessionId: z.string(),
  label: z.string(),
  confidence: z.number().min(0).max(1),
  stable: z.boolean(),
  handsDetected: z.object({
    left: z.boolean(),
    right: z.boolean(),
  }),
  timestampMs: z.number(),
});

export type WsPredictionMessage = z.infer<typeof wsPredictionMessageSchema>;

export const wsStatusMessageSchema = z.object({
  type: z.literal("status"),
  sessionId: z.string(),
  status: z.enum(["connected", "buffering", "ready", "error"]),
  message: z.string().optional(),
});

export type WsStatusMessage = z.infer<typeof wsStatusMessageSchema>;

export const wsServerMessageSchema = z.union([
  wsPredictionMessageSchema,
  wsStatusMessageSchema,
]);

export type WsServerMessage = z.infer<typeof wsServerMessageSchema>;

/**
 * A finalized transcript entry — one recognized sign/word, persisted
 * after a session ends (or periodically) so a user can review history.
 */
export const transcriptEntrySchema = z.object({
  label: z.string(),
  confidence: z.number(),
  spokenAt: z.string(), // ISO timestamp
});

export type TranscriptEntry = z.infer<typeof transcriptEntrySchema>;

export const createSessionSchema = z.object({
  title: z.string().max(200).optional(),
});

export type CreateSessionInput = z.infer<typeof createSessionSchema>;

export const finalizeSessionSchema = z.object({
  transcript: z.array(transcriptEntrySchema),
  durationMs: z.number().nonnegative(),
});

export type FinalizeSessionInput = z.infer<typeof finalizeSessionSchema>;

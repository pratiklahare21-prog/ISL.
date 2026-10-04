import {
  pgTable,
  uuid,
  varchar,
  timestamp,
  integer,
  real,
  jsonb,
} from "drizzle-orm/pg-core";
import { users } from "./users.schema";

/**
 * One live-translation session (webcam turned on until turned off / tab
 * closed). We store a summary + full transcript as jsonb rather than a
 * separate row per sign — a session realistically has tens to low
 * hundreds of entries, so jsonb keeps this simple and avoids N+1 queries
 * on the history page.
 */
export const translationSessions = pgTable("translation_sessions", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id")
    .references(() => users.id, { onDelete: "cascade" })
    .notNull(),
  title: varchar("title", { length: 200 }),
  durationMs: integer("duration_ms").notNull().default(0),
  signCount: integer("sign_count").notNull().default(0),
  avgConfidence: real("avg_confidence"),
  transcript: jsonb("transcript").$type<
    Array<{ label: string; confidence: number; spokenAt: string }>
  >().notNull().default([]),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export type TranslationSession = typeof translationSessions.$inferSelect;
export type NewTranslationSession = typeof translationSessions.$inferInsert;

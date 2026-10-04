import { Router } from "express";
import { createSessionSchema, finalizeSessionSchema } from "@isl/shared";
import { validateBody } from "../middleware/validate";
import { requireAuth } from "../middleware/auth.middleware";
import { asyncHandler } from "../utils/asyncHandler";
import {
  createSession,
  finalizeSession,
  listSessions,
  getSession,
} from "../controllers/sessions.controller";

const router = Router();

router.use(requireAuth);

router.post("/", validateBody(createSessionSchema), asyncHandler(createSession));
router.get("/", asyncHandler(listSessions));
router.get("/:id", asyncHandler(getSession));
router.patch(
  "/:id/finalize",
  validateBody(finalizeSessionSchema),
  asyncHandler(finalizeSession)
);

export default router;

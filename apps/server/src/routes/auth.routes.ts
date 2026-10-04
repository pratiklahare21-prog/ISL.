import { Router } from "express";
import { registerSchema, loginSchema } from "@isl/shared";
import { validateBody } from "../middleware/validate";
import { requireAuth } from "../middleware/auth.middleware";
import { asyncHandler } from "../utils/asyncHandler";
import { register, login, me } from "../controllers/auth.controller";

const router = Router();

router.post("/register", validateBody(registerSchema), asyncHandler(register));
router.post("/login", validateBody(loginSchema), asyncHandler(login));
router.get("/me", requireAuth, asyncHandler(me));

export default router;

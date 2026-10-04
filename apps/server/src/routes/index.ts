import { Router } from "express";
import authRoutes from "./auth.routes";
import sessionsRoutes from "./sessions.routes";
import mlStatusRoutes from "./mlStatus.routes";

const router = Router();

router.use("/auth", authRoutes);
router.use("/sessions", sessionsRoutes);
router.use("/ml", mlStatusRoutes);

export default router;

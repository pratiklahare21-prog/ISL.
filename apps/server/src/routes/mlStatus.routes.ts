import { Router } from "express";
import { env } from "../config/env";
import { asyncHandler } from "../utils/asyncHandler";

const router = Router();

router.get(
  "/status",
  asyncHandler(async (_req, res) => {
    try {
      const response = await fetch(`${env.ML_SERVICE_URL}/health`, {
        signal: AbortSignal.timeout(3000),
      });
      const data = await response.json();
      return res.json({ success: true, data: { reachable: true, ...data } });
    } catch {
      return res.json({
        success: true,
        data: { reachable: false, message: "ml-service is not reachable" },
      });
    }
  })
);

export default router;

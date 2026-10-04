import { Request, Response, NextFunction } from "express";
import { verifyToken, JwtPayload } from "../utils/jwt";
import { ApiError } from "../utils/ApiError";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

export function requireAuth(req: Request, _res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith("Bearer ")) {
    return next(ApiError.unauthorized("Missing or invalid authorization header"));
  }
  const token = header.slice("Bearer ".length);
  try {
    const payload = verifyToken(token);
    req.user = payload;
    next();
  } catch {
    next(ApiError.unauthorized("Invalid or expired token"));
  }
}

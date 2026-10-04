import { Request, Response, NextFunction } from "express";
import { AnyZodObject, ZodError } from "zod";
import { ApiError } from "../utils/ApiError";

export function validateBody(schema: AnyZodObject) {
  return (req: Request, _res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      const err = result.error as ZodError;
      return next(
        ApiError.badRequest("Validation failed", err.flatten().fieldErrors)
      );
    }
    req.body = result.data;
    next();
  };
}

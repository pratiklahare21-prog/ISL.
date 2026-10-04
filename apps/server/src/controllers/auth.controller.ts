import { Request, Response } from "express";
import { eq } from "drizzle-orm";
import { db } from "../db/client";
import { users } from "../db/schema";
import { hashPassword, comparePassword } from "../utils/password";
import { signToken } from "../utils/jwt";
import { ApiError } from "../utils/ApiError";
import type { RegisterInput, LoginInput } from "@isl/shared";

export async function register(req: Request, res: Response) {
  const { name, email, password } = req.body as RegisterInput;

  const existing = await db.query.users.findFirst({
    where: eq(users.email, email.toLowerCase()),
  });
  if (existing) {
    throw ApiError.conflict("An account with this email already exists");
  }

  const passwordHash = await hashPassword(password);
  const [created] = await db
    .insert(users)
    .values({ name, email: email.toLowerCase(), passwordHash })
    .returning();

  const token = signToken({ userId: created.id, role: created.role });

  return res.status(201).json({
    success: true,
    data: {
      token,
      user: {
        id: created.id,
        name: created.name,
        email: created.email,
        role: created.role,
        createdAt: created.createdAt.toISOString(),
      },
    },
  });
}

export async function login(req: Request, res: Response) {
  const { email, password } = req.body as LoginInput;

  const user = await db.query.users.findFirst({
    where: eq(users.email, email.toLowerCase()),
  });
  if (!user) {
    throw ApiError.unauthorized("Invalid email or password");
  }

  const valid = await comparePassword(password, user.passwordHash);
  if (!valid) {
    throw ApiError.unauthorized("Invalid email or password");
  }

  const token = signToken({ userId: user.id, role: user.role });

  return res.json({
    success: true,
    data: {
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        createdAt: user.createdAt.toISOString(),
      },
    },
  });
}

export async function me(req: Request, res: Response) {
  const user = await db.query.users.findFirst({
    where: eq(users.id, req.user!.userId),
  });
  if (!user) throw ApiError.notFound("User not found");

  return res.json({
    success: true,
    data: {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      createdAt: user.createdAt.toISOString(),
    },
  });
}

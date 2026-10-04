/**
 * The default label set the model is trained against. This list is the
 * single source of truth shared between the Python training pipeline
 * (ml/training/labels.py generates from this conceptually) and the
 * frontend (for displaying "known signs" / dataset-collection UI).
 *
 * IMPORTANT: If you change this list, you must re-run dataset collection
 * and retraining — the model's output layer size depends on it.
 * Keep apps/ml-service and ml/training's label list in sync with this file
 * (see ml/training/labels.py which mirrors this exact list).
 */

export const ALPHABET_SIGNS = [
  "A","B","C","D","E","F","G","H","I","J","K","L","M",
  "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
] as const;

export const DIGIT_SIGNS = [
  "0","1","2","3","4","5","6","7","8","9",
] as const;

/** Common daily-conversation words/phrases (dynamic, two-hand signs). */
export const WORD_SIGNS = [
  "HELLO",
  "THANK_YOU",
  "PLEASE",
  "YES",
  "NO",
  "SORRY",
  "HELP",
  "WATER",
  "FOOD",
  "NAME",
  "HOW_ARE_YOU",
  "GOOD",
  "BAD",
  "STOP",
  "GO",
  "COME",
  "WAIT",
  "UNDERSTAND",
  "NOT_UNDERSTAND",
  "MY",
  "YOU",
  "WHERE",
  "WHAT",
  "WHEN",
  "TOILET",
  "HOME",
  "SCHOOL",
  "WORK",
  "FRIEND",
  "FAMILY",
] as const;

export const ALL_SIGN_LABELS = [
  ...ALPHABET_SIGNS,
  ...DIGIT_SIGNS,
  ...WORD_SIGNS,
] as const;

export type SignLabel = (typeof ALL_SIGN_LABELS)[number];

/** Static (single-frame hand-shape) vs dynamic (motion-sequence) signs.
 *  This matters for both dataset collection UX and model windowing. */
export const STATIC_SIGNS: readonly string[] = [...ALPHABET_SIGNS, ...DIGIT_SIGNS];
export const DYNAMIC_SIGNS: readonly string[] = [...WORD_SIGNS];

export function isStaticSign(label: string): boolean {
  return STATIC_SIGNS.includes(label);
}

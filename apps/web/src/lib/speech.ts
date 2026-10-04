/**
 * Thin wrapper over the browser's Web Speech API (speechSynthesis).
 * Queues utterances so overlapping "stable" predictions don't cut each
 * other off mid-word.
 */

const synth = window.speechSynthesis;

export function speak(text: string, opts?: { rate?: number; lang?: string }) {
  if (!synth) return;
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(humanize(text));
  utterance.rate = opts?.rate ?? 0.7;
  utterance.lang = opts?.lang ?? "en-IN";
  utterance.volume = 1;
  synth.speak(utterance);
}

export function stopSpeaking() {
  synth?.cancel();
}

/** Converts internal labels like "THANK_YOU" / "HOW_ARE_YOU" into
 *  natural spoken phrases. Single letters/digits are spoken as-is. */
function humanize(label: string): string {
  if (label.length === 1) {
    if (/^\d$/.test(label)) return label;
    const letterNames: Record<string, string> = {
      A: "ay", B: "bee", C: "see", D: "dee", E: "ee", F: "ef",
      G: "jee", H: "aitch", I: "eye", J: "jay", K: "kay", L: "el",
      M: "em", N: "en", O: "oh", P: "pee", Q: "cue", R: "ar",
      S: "ess", T: "tee", U: "you", V: "vee", W: "double you",
      X: "ex", Y: "why", Z: "zee",
    };
    return letterNames[label.toUpperCase()] ?? label;
  }
  return label.replace(/_/g, " ").toLowerCase();
}

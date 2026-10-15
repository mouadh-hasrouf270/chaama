import { useEffect, useState } from "react";

type Phase = "typing" | "deleting";

type Line = {
  text: string;
  accent?: boolean;
};

const EXPRESSIONS: Line[][] = [
  [
    { text: "Votre expertise" },
    { text: "juridique," },
    { text: "au service", accent: true },
    { text: "de vos intérêts." },
  ],
  [
    { text: "Votre cabinet" },
    { text: "à vos côtés," },
    { text: "chaque jour", accent: true },
    { text: "pour vos affaires." },
  ],
];

export function TypewriterHeading() {
  const [expressionIndex, setExpressionIndex] = useState(0);
  const [revealed, setRevealed] = useState(0);
  const [phase, setPhase] = useState<Phase>("typing");

  const expression = EXPRESSIONS[expressionIndex];

  const fullText = expression.map((line) => line.text).join("");

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    if (phase === "typing") {
      if (revealed < fullText.length) {
        const nextChar = fullText[revealed];

        const delay = nextChar === "," || nextChar === "." ? 220 : 42;

        timer = setTimeout(() => {
          setRevealed((value) => value + 1);
        }, delay);
      } else {
        timer = setTimeout(() => {
          setPhase("deleting");
        }, 2200);
      }
    } else {
      if (revealed > 0) {
        timer = setTimeout(() => {
          setRevealed((value) => value - 1);
        }, 22);
      } else {
        timer = setTimeout(() => {
          setExpressionIndex((index) => (index + 1) % EXPRESSIONS.length);

          setPhase("typing");
        }, 500);
      }
    }

    return () => clearTimeout(timer);
  }, [revealed, phase, fullText]);

  return (
    <h1
      className="
        font-serif
        text-[48px]
        font-normal
        leading-[0.9]
        sm:text-[40px]
        lg:text-[80px]
      "
    >
      {expression.map((line, index) => {
        // Calcule la position de départ de cette ligne
        const start = expression
          .slice(0, index)
          .reduce((total, currentLine) => total + currentLine.text.length, 0);

        const shown = Math.max(0, Math.min(line.text.length, revealed - start));

        return (
          <span key={`${expressionIndex}-${index}`}>
            <span className={line.accent ? "text-[#C79C57]" : undefined}>
              {line.text.slice(0, shown)}
            </span>

            {index < expression.length - 1 && <br />}
          </span>
        );
      })}

      <span
        className="
          inline-block
          w-[0.5ch]
          h-[0.85em]
          bg-[#C79C57]
          ml-1
          align-text-bottom
        "
        style={{
          animation: "caret-blink 1s steps(1) infinite",
        }}
      />
    </h1>
  );
}

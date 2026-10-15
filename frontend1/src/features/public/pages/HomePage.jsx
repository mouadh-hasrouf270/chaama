import { motion } from "framer-motion";

import HeroSection from "../sections/HeroSection";
import StatsBar from "../sections/StatsBar";
import CabinetSection from "../sections/CabinetSection";
import ExpertiseSection from "../sections/ExpertiseSection";
import ValuesSection from "../sections/ValuesSection";
import QuoteSection from "../sections/QuoteSection";
import ContactSection from "../sections/ContactSection";

const sectionAnimation = {
  initial: { opacity: 0, y: 60 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.15 },
  transition: { duration: 0.7, ease: "easeOut" },
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[var(--chaama-cream)] text-[var(--chaama-text)]">
      <motion.div {...sectionAnimation}>
        <HeroSection />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <StatsBar />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <CabinetSection />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <ExpertiseSection />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <ValuesSection />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <QuoteSection />
      </motion.div>

      <motion.div {...sectionAnimation}>
        <ContactSection />
      </motion.div>
    </div>
  );
}

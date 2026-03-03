"use client";

import { useState } from "react";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FeatureFlagsModal } from "@/components/FeatureFlagsModal";

export function DevSettingsButton() {
  const [modalOpen, setModalOpen] = useState(false);

  if (process.env.NEXT_PUBLIC_DEV_MODE !== "true") {
    return null;
  }

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        className="fixed bottom-4 left-4 z-40 h-10 w-10 rounded-full shadow-lg"
        onClick={() => setModalOpen(true)}
        aria-label="Developer Settings"
      >
        <Settings className="h-5 w-5" />
      </Button>
      <FeatureFlagsModal open={modalOpen} onOpenChange={setModalOpen} />
    </>
  );
}

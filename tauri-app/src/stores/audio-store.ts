import { create } from "zustand";

interface AudioState {
  isPlaying: boolean;
  currentFrequency: number;
  currentLevel: number;
  currentChannel: "left" | "right";
  transducer: "air" | "bone";
  setPlaying: (playing: boolean) => void;
  setFrequency: (freq: number) => void;
  setLevel: (level: number) => void;
  setChannel: (channel: "left" | "right") => void;
  setTransducer: (transducer: "air" | "bone") => void;
}

export const useAudioStore = create<AudioState>((set) => ({
  isPlaying: false,
  currentFrequency: 1000,
  currentLevel: 40,
  currentChannel: "right",
  transducer: "air",

  setPlaying: (playing) => set({ isPlaying: playing }),
  setFrequency: (freq) => set({ currentFrequency: freq }),
  setLevel: (level) => set({ currentLevel: level }),
  setChannel: (channel) => set({ currentChannel: channel }),
  setTransducer: (transducer) => set({ transducer }),
}));

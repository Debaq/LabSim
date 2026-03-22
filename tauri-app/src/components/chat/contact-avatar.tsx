import { cn } from "@/lib/utils";

interface ContactAvatarProps {
  avatar: string;
  color?: string;
  size?: "sm" | "md" | "lg";
}

const SIZES = {
  sm: "h-8 w-8 text-xs",
  md: "h-9 w-9 text-xs",
  lg: "h-11 w-11 text-sm",
};

function isImagePath(avatar: string) {
  return avatar.startsWith("/") || avatar.startsWith("http");
}

export function ContactAvatar({ avatar, color, size = "md" }: ContactAvatarProps) {
  const sizeClass = SIZES[size];

  if (isImagePath(avatar)) {
    return (
      <img
        src={avatar}
        alt=""
        className={cn("rounded-full object-cover", sizeClass)}
        draggable={false}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-gradient-to-br font-bold ls-text",
        sizeClass,
        color,
      )}
    >
      {avatar}
    </div>
  );
}

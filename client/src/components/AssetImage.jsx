import React, { useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const AssetImage = ({ src, alt, className, fallbackIcon: FallbackIcon = ImageIcon }) => {
  const [error, setError] = useState(false);

  if (error || !src) {
    return (
      <div className={cn("flex flex-col items-center justify-center bg-border/30 rounded-lg text-muted", className)}>
        <FallbackIcon size={32} className="mb-2 opacity-50" />
        <span className="text-xs font-medium px-4 text-center">{alt || 'Image missing'}</span>
      </div>
    );
  }

  return (
    <img 
      src={src} 
      alt={alt} 
      onError={() => setError(true)} 
      className={cn("object-cover", className)}
    />
  );
};

export default AssetImage;

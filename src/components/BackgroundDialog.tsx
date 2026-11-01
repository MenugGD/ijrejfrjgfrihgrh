import React, { useState } from 'react';
import { Image, Upload, X } from 'lucide-react';

interface BackgroundDialogProps {
  currentBg: {
    media: string;
    blur: number;
    veil: number;
  };
  onSave: (bg: { media: string; blur: number; veil: number }) => void;
  onClose: () => void;
}

export const BackgroundDialog: React.FC<BackgroundDialogProps> = ({
  currentBg,
  onSave,
  onClose,
}) => {
  const [media, setMedia] = useState<string>(currentBg.media);
  const [blur, setBlur] = useState<number>(currentBg.blur);
  const [veil, setVeil] = useState<number>(currentBg.veil);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setMedia(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemove = () => {
    setMedia('');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-neutral-100 hover:bg-neutral-200 text-neutral-600 flex items-center justify-center cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        <h3 className="text-xl font-bold text-neutral-900 mb-4">
          Fondo personalizado
        </h3>

        <div className="space-y-4">
          <div className="flex gap-2">
            <label className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-[#FFF1E6] hover:bg-[#FFE0C7] text-[#E8590C] rounded-xl text-xs font-bold cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              Elegir imagen…
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>

            <button
              type="button"
              onClick={handleRemove}
              className="py-2.5 px-4 bg-neutral-100 hover:bg-neutral-200 text-neutral-600 rounded-xl text-xs font-bold cursor-pointer transition-colors"
            >
              Quitar fondo
            </button>
          </div>

          {/* URL Input */}
          <div>
            <label className="block text-xs font-bold text-neutral-500 mb-1">
              O pegar URL de imagen
            </label>
            <input
              type="text"
              value={media}
              onChange={(e) => setMedia(e.target.value)}
              placeholder="https://..."
              className="w-full bg-neutral-50 border border-neutral-300 focus:border-[#FF7A1A] rounded-xl px-3 py-2 text-xs font-mono focus:outline-none"
            />
          </div>

          {/* Blur Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold text-neutral-700 mb-1">
              <span>Desenfoque (blur):</span>
              <span>{blur}px</span>
            </div>
            <input
              type="range"
              min="0"
              max="40"
              value={blur}
              onChange={(e) => setBlur(Number(e.target.value))}
              className="w-full accent-[#FF7A1A]"
            />
          </div>

          {/* Veil Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold text-neutral-700 mb-1">
              <span>Velo blanco (legibilidad):</span>
              <span>{veil}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="90"
              value={veil}
              onChange={(e) => setVeil(Number(e.target.value))}
              className="w-full accent-[#FF7A1A]"
            />
          </div>

          {/* Preview */}
          <div className="w-full h-28 rounded-xl overflow-hidden border border-neutral-200 relative bg-neutral-100 flex items-center justify-center">
            {media ? (
              <>
                <img src={media} alt="" className="w-full h-full object-cover" />
                <div
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    backgroundColor: `rgba(255, 255, 255, ${(veil * 2.55) / 255})`,
                    backdropFilter: blur > 0 ? `blur(${blur}px)` : 'none',
                  }}
                />
                <span className="relative z-10 text-xs font-bold text-[#2B2B2B] bg-white/80 px-2 py-0.5 rounded">
                  Vista Previa
                </span>
              </>
            ) : (
              <span className="text-xs text-neutral-400 font-medium">
                Sin imagen de fondo (fondo por defecto)
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 mt-6 pt-4 border-t border-neutral-100">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-full text-xs font-bold cursor-pointer"
          >
            Cancelar
          </button>
          <button
            onClick={() => {
              onSave({ media, blur, veil });
              onClose();
            }}
            className="px-5 py-2 bg-[#FF7A1A] hover:bg-[#FF8D3A] text-white rounded-full text-xs font-bold shadow-md cursor-pointer"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
};

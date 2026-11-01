import React, { useState } from 'react';
import { Participant } from '../types';
import { Camera, Edit3, Image, Upload, X } from 'lucide-react';

interface SlotPreviewModalProps {
  slotKey: string;
  participant: Participant | null;
  onSave: (participant: Participant | null) => void;
  onClose: () => void;
  onToggleEliminated?: () => void;
  isEliminated?: boolean;
}

export const SlotPreviewModal: React.FC<SlotPreviewModalProps> = ({
  slotKey,
  participant,
  onSave,
  onClose,
  onToggleEliminated,
  isEliminated = false,
}) => {
  const [name, setName] = useState<string>(participant?.name || '');
  const [detail, setDetail] = useState<string>(participant?.detail || '');
  const [media, setMedia] = useState<string>(participant?.media || '');
  const [isEditing, setIsEditing] = useState<boolean>(!participant);

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

  const handleSave = () => {
    if (!name.trim() && !media.trim()) {
      onSave(null);
    } else {
      onSave({
        name: name.trim() || 'Participante',
        detail: detail.trim(),
        media: media || 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80',
        fx: participant?.fx ?? 0.5,
        fy: participant?.fy ?? 0.5,
        zoom: participant?.zoom ?? 1.0,
      });
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-white rounded-3xl p-5 sm:p-7 max-w-lg w-full shadow-2xl relative my-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-9 h-9 rounded-full bg-neutral-100 hover:bg-neutral-200 text-neutral-600 flex items-center justify-center transition-all cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-neutral-900 mb-4 flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-[#FF7A1A]" />
          Casilla {slotKey}
        </h3>

        {/* Media Preview */}
        <div className="relative aspect-[16/10] rounded-2xl overflow-hidden border-2 border-[#FF7A1A]/40 mb-4 bg-neutral-100 shadow-inner">
          {media ? (
            <img src={media} alt={name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-neutral-400 gap-2">
              <Image className="w-10 h-10 text-neutral-300" />
              <span className="text-xs font-semibold">Sin imagen asignada</span>
            </div>
          )}

          {isEliminated && (
            <div className="absolute inset-0 bg-neutral-900/80 flex items-center justify-center">
              <span className="bg-red-600 text-white font-extrabold text-xs px-3 py-1 rounded">
                ELIMINADO
              </span>
            </div>
          )}
        </div>

        {/* Form Fields */}
        <div className="space-y-3.5">
          <div>
            <label className="block text-xs font-bold text-neutral-600 mb-1">
              Nombre de la Obra o Personaje
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: Dragón Místico"
              className="w-full bg-neutral-50 border-2 border-neutral-200 focus:border-[#FF7A1A] rounded-xl px-3.5 py-2 text-sm text-neutral-900 focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-neutral-600 mb-1">
              Detalle / Artista
            </label>
            <input
              type="text"
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              placeholder="Ej: Ilustrado por Elena"
              className="w-full bg-neutral-50 border-2 border-neutral-200 focus:border-[#FF7A1A] rounded-xl px-3.5 py-2 text-sm text-neutral-900 focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-neutral-600 mb-1">
              Subir Imagen desde el móvil u ordenador
            </label>
            <label className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-orange-50 hover:bg-orange-100 border border-dashed border-[#FF7A1A] text-[#E8590C] rounded-xl text-xs font-bold cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              Seleccionar foto o dibujo
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          <div>
            <label className="block text-xs font-bold text-neutral-600 mb-1">
              O pegar URL de imagen
            </label>
            <input
              type="text"
              value={media}
              onChange={(e) => setMedia(e.target.value)}
              placeholder="https://ejemplo.com/dibujo.jpg"
              className="w-full bg-neutral-50 border-2 border-neutral-200 focus:border-[#FF7A1A] rounded-xl px-3.5 py-2 text-xs text-neutral-900 font-mono focus:outline-none transition-colors"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-6 pt-4 border-t border-neutral-100">
          {onToggleEliminated && participant && (
            <button
              type="button"
              onClick={onToggleEliminated}
              className="w-full sm:w-auto text-xs font-bold text-neutral-500 hover:text-neutral-800 underline py-1"
            >
              {isEliminated ? 'Quitar eliminado' : 'Marcar eliminado'}
            </button>
          )}

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 sm:flex-none px-4 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-full text-xs font-bold transition-colors cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="flex-1 sm:flex-none px-5 py-2 bg-[#FF7A1A] hover:bg-[#FF8D3A] text-white rounded-full text-xs font-bold shadow-md transition-all cursor-pointer"
            >
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

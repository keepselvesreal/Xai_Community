import { useState, useCallback } from "react";
import type { ModalState } from "~/types";

interface UseModalOptions {
  defaultOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
}

export function useModal(options: UseModalOptions = {}) {
  const { defaultOpen = false, onOpen, onClose } = options;
  
  const [modalState, setModalState] = useState<ModalState>({
    isOpen: defaultOpen,
    title: undefined,
    content: undefined,
    onClose: undefined,
  });

  const openModal = useCallback((
    title?: string, 
    content?: React.ReactNode,
    customOnClose?: () => void
  ) => {
    setModalState({
      isOpen: true,
      title,
      content,
      onClose: customOnClose,
    });
    onOpen?.();
  }, [onOpen]);

  const closeModal = useCallback(() => {
    setModalState(prev => ({
      ...prev,
      isOpen: false,
    }));
    
    // 사용자 정의 onClose 호출
    if (modalState.onClose) {
      modalState.onClose();
    }
    
    onClose?.();
  }, [modalState.onClose, onClose]);

  const updateModal = useCallback((updates: Partial<Omit<ModalState, 'isOpen'>>) => {
    setModalState(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  return {
    isOpen: modalState.isOpen,
    title: modalState.title,
    content: modalState.content,
    openModal,
    closeModal,
    updateModal,
  };
}

export default useModal;
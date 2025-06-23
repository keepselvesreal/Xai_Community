import { useState, useEffect, useCallback } from "react";
import { getLocalStorage, setLocalStorage, removeLocalStorage } from "~/lib/utils";

export function useLocalStorage<T>(key: string, defaultValue: T) {
  const [value, setValue] = useState<T>(() => {
    return getLocalStorage(key, defaultValue);
  });

  const updateValue = useCallback((newValue: T | ((prev: T) => T)) => {
    setValue(prevValue => {
      const valueToStore = typeof newValue === 'function' 
        ? (newValue as (prev: T) => T)(prevValue)
        : newValue;
      
      setLocalStorage(key, valueToStore);
      return valueToStore;
    });
  }, [key]);

  const removeValue = useCallback(() => {
    removeLocalStorage(key);
    setValue(defaultValue);
  }, [key, defaultValue]);

  // 다른 탭에서 localStorage가 변경될 때 동기화
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setValue(JSON.parse(e.newValue));
        } catch {
          // JSON 파싱 실패시 기본값 사용
          setValue(defaultValue);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, defaultValue]);

  return [value, updateValue, removeValue] as const;
}

export default useLocalStorage;
import { useState, useCallback } from "react";
import type { FormState } from "~/types";

interface UseFormOptions<T> {
  initialValues: T;
  validate?: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => Promise<void> | void;
}

export function useForm<T extends Record<string, any>>({
  initialValues,
  validate,
  onSubmit,
}: UseFormOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [formState, setFormState] = useState<FormState>({
    isSubmitting: false,
    errors: {},
    touched: {},
  });

  const setValue = useCallback((name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // 필드가 터치되었음을 표시
    setFormState(prev => ({
      ...prev,
      touched: { ...prev.touched, [name]: true },
      // 에러가 있다면 재검증
      errors: validate ? { ...prev.errors, ...validate({ ...values, [name]: value }) } : prev.errors,
    }));
  }, [values, validate]);

  const setFieldError = useCallback((name: keyof T, error: string) => {
    setFormState(prev => ({
      ...prev,
      errors: { ...prev.errors, [name]: error },
    }));
  }, []);

  const clearFieldError = useCallback((name: keyof T) => {
    setFormState(prev => ({
      ...prev,
      errors: { ...prev.errors, [name]: undefined },
    }));
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setFormState({
      isSubmitting: false,
      errors: {},
      touched: {},
    });
  }, [initialValues]);

  const handleSubmit = useCallback(async (event?: React.FormEvent) => {
    if (event) {
      event.preventDefault();
    }

    // 모든 필드를 터치됨으로 표시
    const touchedFields = Object.keys(values).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {} as Record<string, boolean>);

    setFormState(prev => ({ ...prev, touched: touchedFields }));

    // 유효성 검사
    const errors = validate ? validate(values) : {};
    const hasErrors = Object.values(errors).some(error => !!error);

    if (hasErrors) {
      setFormState(prev => ({ ...prev, errors }));
      return;
    }

    // 제출
    setFormState(prev => ({ ...prev, isSubmitting: true, errors: {} }));
    
    try {
      await onSubmit(values);
    } catch (error) {
      // 서버 에러 처리
      if (error instanceof Error) {
        setFormState(prev => ({
          ...prev,
          errors: { _form: error.message },
        }));
      }
    } finally {
      setFormState(prev => ({ ...prev, isSubmitting: false }));
    }
  }, [values, validate, onSubmit]);

  const getFieldProps = useCallback((name: keyof T) => ({
    name: name as string,
    value: values[name] || "",
    onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setValue(name, event.target.value);
    },
    onBlur: () => {
      setFormState(prev => ({
        ...prev,
        touched: { ...prev.touched, [name]: true },
      }));
    },
    error: formState.touched[name] ? formState.errors[name] : undefined,
  }), [values, formState, setValue]);

  const isValid = Object.values(formState.errors).every(error => !error);
  const isDirty = JSON.stringify(values) !== JSON.stringify(initialValues);

  return {
    values,
    formState,
    setValue,
    setFieldError,
    clearFieldError,
    reset,
    handleSubmit,
    getFieldProps,
    isValid,
    isDirty,
  };
}

export default useForm;
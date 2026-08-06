'use client';

import type React from 'react';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { useTranslation } from 'react-i18next';
import i18n from '@/i18n';
import { useAuth } from '@/hooks/useAuth';

import type { UserInfo } from '@/c-types';

interface EmployeeLoginProps {
  onLoginSuccess: (userInfo: UserInfo) => void;
  loginContext?: string;
}

/**
 * Employee (AAD) login form — the primary enterprise entry under AAD
 * strong-login control. Mirrors the backend `POST /api/user/login_employee`
 * route (employeeNo + password, AAD_BYPASS=1 accepts any password in dev).
 */
export function EmployeeLogin({ onLoginSuccess, loginContext }: EmployeeLoginProps) {
  const { toast } = useToast();
  const { t } = useTranslation();
  const { loginWithEmployee } = useAuth({
    onSuccess: onLoginSuccess,
    loginContext,
  });

  const [employeeNo, setEmployeeNo] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [employeeNoError, setEmployeeNoError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const handleEmployeeNoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmployeeNo(value);
    if (value) setEmployeeNoError('');
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    if (value) setPasswordError('');
  };

  const doLogin = async () => {
    const trimmedNo = employeeNo.trim();
    let hasError = false;
    if (!trimmedNo) {
      setEmployeeNoError(t('module.auth.employeeNoEmpty'));
      hasError = true;
    }
    if (!password) {
      setPasswordError(t('module.auth.passwordEmpty'));
      hasError = true;
    }
    if (hasError) return;

    setIsLoading(true);
    try {
      await loginWithEmployee(trimmedNo, password, i18n.language);
    } catch {
      // Error toast is already shown by the auth hook.
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='space-y-4'>
      <div className='space-y-2'>
        <Label htmlFor='employeeNo'>
          {t('module.auth.employeeNo')}
        </Label>
        <Input
          id='employeeNo'
          name='employeeNo'
          type='text'
          autoComplete='username'
          placeholder={t('module.auth.employeeNoPlaceholder')}
          value={employeeNo}
          onChange={handleEmployeeNoChange}
          disabled={isLoading}
          aria-invalid={!!employeeNoError}
        />
        {employeeNoError && (
          <p className='text-sm text-red-500'>{employeeNoError}</p>
        )}
      </div>

      <div className='space-y-2'>
        <Label htmlFor='employee-password'>
          {t('module.auth.password')}
        </Label>
        <div className='relative'>
          <Input
            id='employee-password'
            type={showPassword ? 'text' : 'password'}
            autoComplete='current-password'
            placeholder={t('module.auth.passwordPlaceholder')}
            value={password}
            onChange={handlePasswordChange}
            disabled={isLoading}
            aria-invalid={!!passwordError}
            onKeyDown={e => {
              if (e.key === 'Enter' && !isLoading) {
                doLogin();
              }
            }}
          />
          <button
            type='button'
            aria-label='toggle password visibility'
            className='absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground'
            onClick={() => setShowPassword(prev => !prev)}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {passwordError && (
          <p className='text-sm text-red-500'>{passwordError}</p>
        )}
      </div>

      <Button
        type='button'
        className='w-full'
        onClick={() => doLogin()}
        disabled={isLoading}
      >
        {isLoading ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : null}
        {t('module.auth.login')}
      </Button>
    </div>
  );
}

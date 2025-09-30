'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { PhoneLogin } from '@/components/auth/PhoneLogin';
import { EmailLogin } from '@/components/auth/EmailLogin';
import { FeedbackForm } from '@/components/auth/FeedbackForm';
import Image from 'next/image';
import logoHorizontal from '@/c-assets/logos/ai-shifu-logo-horizontal.png';
import LanguageSelect from '@/components/language-select';
import { useTranslation } from 'react-i18next';
import i18n, { browserLanguage, normalizeLanguage } from '@/i18n';
import { environment } from '@/config/environment';
import { useUserStore } from '@/store';

export default function AuthPage() {
  const router = useRouter();
  const [authMode, setAuthMode] = useState<'login' | 'feedback'>('login');
  const [isI18nReady, setIsI18nReady] = useState(false);
  const { userInfo, isInitialized } = useUserStore();

  // Get login methods from environment configuration
  const enabledMethods = environment.loginMethodsEnabled;
  const defaultMethod = environment.defaultLoginMethod;

  const isPhoneEnabled = enabledMethods.includes('phone');
  const isEmailEnabled = enabledMethods.includes('email');

  const [loginMethod, setLoginMethod] = useState<'phone' | 'email'>(
    defaultMethod as 'phone' | 'email',
  );
  const [language, setLanguage] = useState<string | null>(null);
  const manualLanguageRef = useRef(false);

  const searchParams = useSearchParams();
  const handleAuthSuccess = () => {
    let redirect = searchParams.get('redirect');
    if (!redirect || redirect.charAt(0) !== '/') {
      redirect = '/main';
    }
    // Using push for navigation keeps a history, so when users click the back button, they'll return to the login page.
    // router.push('/main')
    router.replace(redirect);
  };

  const handleFeedback = () => {
    setAuthMode('feedback');
  };

  const handleBackToLogin = () => {
    setAuthMode('login');
  };

  const { t, ready } = useTranslation();

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    const preferred = userInfo?.language
      ? normalizeLanguage(userInfo.language)
      : null;
    const nextLanguage = normalizeLanguage(preferred ?? browserLanguage);

    if (!nextLanguage) {
      return;
    }

    if (language === nextLanguage) {
      manualLanguageRef.current = false;
      return;
    }

    if (manualLanguageRef.current) {
      return;
    }

    let isCancelled = false;

    setIsI18nReady(false);

    const applyLanguage = async () => {
      try {
        await i18n.changeLanguage(nextLanguage);
        if (!isCancelled) {
          setLanguage(nextLanguage);
        }
      } catch (error) {
        console.error('Failed to change language', error);
      }
    };

    applyLanguage();

    return () => {
      isCancelled = true;
    };
  }, [browserLanguage, isInitialized, language, userInfo]);

  const handleManualLanguageChange = useCallback(
    async (value: string) => {
      const normalized = normalizeLanguage(value);
      if (!normalized || normalized === language) {
        return;
      }

      manualLanguageRef.current = true;
      setIsI18nReady(false);

      try {
        await i18n.changeLanguage(normalized);
        setLanguage(normalized);
      } catch (error) {
        console.error('Failed to change language', error);
      }
    },
    [language],
  );

  // Monitor i18n ready state to prevent language flash
  useEffect(() => {
    if (!language) {
      return;
    }

    const resolvedLanguage = i18n.resolvedLanguage ?? i18n.language;
    const hasBundle = i18n.hasResourceBundle(language, 'translation');

    if (!ready || resolvedLanguage !== language) {
      return;
    }

    if (hasBundle) {
      setIsI18nReady(true);
    }
  }, [language, ready]);

  // Show loading state until translations are ready
  if (!isI18nReady || !language) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900'>
        <div className='w-full max-w-md space-y-2'>
          <div className='flex flex-col items-center'>
            <Image
              className='dark:invert'
              src={logoHorizontal}
              alt='AI-Shifu'
              width={180}
              height={40}
              priority
            />
          </div>
          <Card>
            <CardContent className='flex items-center justify-center py-8'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-primary'></div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }
  return (
    <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4'>
      <div className='w-full max-w-md space-y-2'>
        <div className='flex flex-col items-center relative'>
          <h2 className='text-primary flex items-center font-semibold pb-2  w-full justify-center'>
            <Image
              className='dark:invert'
              src={logoHorizontal}
              alt='AI-Shifu'
              width={180}
              height={40}
              priority
            />

            <div className='absolute top-0 right-0'>
              <LanguageSelect
                language={language}
                onSetLanguage={handleManualLanguageChange}
                variant='login'
              />
            </div>
          </h2>
        </div>
        <Card>
          <CardHeader>
            {authMode === 'login' && (
              <>
                <CardTitle className='text-xl text-center'>
                  {t('auth.title')}
                </CardTitle>
              </>
            )}
            {authMode === 'feedback' && (
              <>
                <CardTitle className='text-xl text-center'>
                  {t('auth.feedback')}
                </CardTitle>
                <CardDescription className='text-sm text-center'>
                  {t('auth.feedback')}
                </CardDescription>
              </>
            )}
          </CardHeader>

          <CardContent>
            {authMode === 'login' && (
              <>
                {enabledMethods.length > 1 ? (
                  <Tabs
                    value={loginMethod}
                    onValueChange={value =>
                      setLoginMethod(value as 'phone' | 'email')
                    }
                    className='w-full'
                  >
                    <TabsList className={'grid w-full grid-cols-2'}>
                      {isPhoneEnabled && (
                        <TabsTrigger value='phone'>
                          {t('auth.phone')}
                        </TabsTrigger>
                      )}
                      {isEmailEnabled && (
                        <TabsTrigger value='email'>
                          {t('auth.email')}
                        </TabsTrigger>
                      )}
                    </TabsList>

                    {isPhoneEnabled && (
                      <TabsContent value='phone'>
                        <PhoneLogin onLoginSuccess={handleAuthSuccess} />
                      </TabsContent>
                    )}

                    {isEmailEnabled && (
                      <TabsContent value='email'>
                        <EmailLogin onLoginSuccess={handleAuthSuccess} />
                      </TabsContent>
                    )}
                  </Tabs>
                ) : (
                  // Single method, no tabs needed
                  <div className='w-full'>
                    {isPhoneEnabled && (
                      <PhoneLogin onLoginSuccess={handleAuthSuccess} />
                    )}
                    {isEmailEnabled && (
                      <EmailLogin onLoginSuccess={handleAuthSuccess} />
                    )}
                  </div>
                )}
              </>
            )}

            {authMode === 'feedback' && (
              <FeedbackForm onComplete={handleBackToLogin} />
            )}
          </CardContent>
          <CardFooter className='flex flex-col items-center space-y-2'>
            {authMode === 'feedback' && (
              <button
                onClick={handleBackToLogin}
                className='text-primary hover:underline'
              >
                {t('auth.backToLogin')}
              </button>
            )}
            {authMode !== 'feedback' && (
              <p className='text-sm text-muted-foreground'>
                {t('auth.problem')}
                <button
                  onClick={handleFeedback}
                  className='text-primary hover:underline'
                >
                  {t('auth.submitFeedback')}
                </button>
              </p>
            )}
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}

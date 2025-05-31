import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/hooks/useAuth';
import { Mail, ArrowRight } from 'lucide-react';

type AuthStep = 'email' | 'otp';

interface EmailForm {
  email: string;
}

interface OTPForm {
  otp: string;
}

export const AuthForm: React.FC = () => {
  const [step, setStep] = useState<AuthStep>('email');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { sendOTP, verifyOTP } = useAuth();

  const emailForm = useForm<EmailForm>();
  const otpForm = useForm<OTPForm>();

  const onSendOTP = async (data: EmailForm) => {
    setLoading(true);
    try {
      const result = await sendOTP(data.email);
      if (result.success) {
        setEmail(data.email);
        setStep('otp');
        toast.success('OTP sent to your email!');
      } else {
        toast.error(result.error || 'Failed to send OTP');
      }
    } catch (error) {
      toast.error('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const onVerifyOTP = async (data: OTPForm) => {
    setLoading(true);
    try {
      const result = await verifyOTP(email, data.otp);
      if (result.success) {
        toast.success('Welcome to DocAnalyzer!');
        window.location.href = '/';
      } else {
        toast.error(result.error || 'Invalid OTP');
      }
    } catch (error) {
      toast.error('An error occurred during verification');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="glass-effect rounded-2xl p-8 shadow-2xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h2 className="text-3xl font-bold text-white mb-2">
            {step === 'email' && 'Welcome to DocAnalyzer'}
            {step === 'otp' && 'Verify Your Email'}
          </h2>
          <p className="text-dark-300">
            {step === 'email' && 'Enter your email to get started'}
            {step === 'otp' && 'Enter the OTP code sent to your email'}
          </p>
        </motion.div>

        {/* Email Step */}
        {step === 'email' && (
          <motion.form
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            onSubmit={emailForm.handleSubmit(onSendOTP)}
            className="space-y-6"
          >
            <Input
              label="Email Address"
              type="email"
              placeholder="Enter your email"
              icon={<Mail />}
              {...emailForm.register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address'
                }
              })}
              error={emailForm.formState.errors.email?.message}
            />

            <Button
              type="submit"
              className="w-full"
              loading={loading}
              icon={<ArrowRight />}
            >
              Send OTP
            </Button>

            <div className="text-center">
              <p className="text-dark-400 text-sm">
                We'll send a verification code to your email
              </p>
            </div>
          </motion.form>
        )}

        {/* OTP Step */}
        {step === 'otp' && (
          <motion.form
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            onSubmit={otpForm.handleSubmit(onVerifyOTP)}
            className="space-y-6"
          >
            <div className="text-center mb-6">
              <p className="text-dark-300">
                We've sent a verification code to
              </p>
              <p className="text-primary-400 font-medium">{email}</p>
            </div>

            <Input
              label="Verification Code"
              type="text"
              placeholder="Enter 6-digit code"
              maxLength={6}
              className="text-center text-2xl tracking-widest"
              {...otpForm.register('otp', { 
                required: 'OTP is required',
                pattern: { value: /^\d{6}$/, message: 'OTP must be 6 digits' }
              })}
              error={otpForm.formState.errors.otp?.message}
            />

            <Button
              type="submit"
              className="w-full"
              loading={loading}
              icon={<ArrowRight />}
            >
              Verify & Sign In
            </Button>

            <div className="text-center space-y-2">
              <button
                type="button"
                onClick={() => {
                  setStep('email');
                  setEmail('');
                  otpForm.reset();
                }}
                className="text-primary-400 hover:text-primary-300 text-sm font-medium"
              >
                Use different email
              </button>
              
              <br />
              
              <button
                type="button"
                onClick={() => onSendOTP({ email })}
                disabled={loading}
                className="text-dark-400 hover:text-dark-300 text-sm"
              >
                Resend OTP
              </button>
            </div>
          </motion.form>
        )}
      </div>
    </div>
  );
};

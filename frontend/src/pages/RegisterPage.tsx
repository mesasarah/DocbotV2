import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { InputField } from "../components/InputField";
import { Button } from "../components/Button";
import { useAuth } from "../hooks/useAuth";
import { extractErrorMessage } from "../api/client";

const schema = z.object({
  full_name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setApiError(null);
    try {
      await registerUser(values.email, values.full_name, values.password);
      const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname;
      navigate(from ?? "/dashboard");
    } catch (err) {
      setApiError(extractErrorMessage(err, "Couldn't create your account."));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-900 px-4">
      <div className="w-full max-w-sm animate-slide-up">
        <div className="mb-8 flex flex-col items-center gap-3">
          <Link to="/" className="flex h-11 w-11 items-center justify-center rounded-lg bg-gradient-to-br from-rose-400 to-rose-600 font-mono text-lg font-bold text-ink-950 shadow-lg shadow-rose-500/20">
            D
          </Link>
          <div className="text-center">
            <h1 className="text-lg font-semibold text-paper-100">Create your account</h1>
            <p className="text-sm text-paper-300">Set up offline document intelligence.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 rounded-xl border border-ink-700 bg-ink-800/40 p-6">
          <InputField label="Full name" autoComplete="name" error={errors.full_name?.message} {...register("full_name")} />
          <InputField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
          <InputField
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register("password")}
          />

          {apiError && (
            <p className="rounded-lg bg-crimson-500/10 px-3 py-2 text-sm text-crimson-400">{apiError}</p>
          )}

          <Button type="submit" isLoading={isSubmitting} className="mt-2 w-full">
            Create account
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-paper-300">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-rose-400 hover:text-rose-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { api } from "../../services/api";
import { useAppStore } from "../../store/useAppStore";
import { ShieldCheck, Mail, Lock, User, ArrowRight, Loader2 } from "lucide-react";

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type RegisterFields = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAppStore((state) => state.setAuth);
  const setUser = useAppStore((state) => state.setUser);
  
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFields>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFields) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // 1. Register User
      await api.post("/auth/register", {
        email: data.email,
        password: data.password,
        full_name: data.full_name,
      });
      
      // 2. Perform auto-login
      const loginResponse = await api.post("/auth/login-json", {
        email: data.email,
        password: data.password,
      });
      const { access_token, refresh_token } = loginResponse.data;
      
      setAuth(access_token, refresh_token);
      
      // 3. Fetch user details
      const userRes = await api.get("/auth/me");
      setUser(userRes.data);
      
      router.push("/dashboard");
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err.response?.data?.detail || "Registration failed. Please check details."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-blue-900/10 blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-violet-900/10 blur-[120px]" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10">
        <Link href="/" className="flex justify-center items-center gap-2 group">
          <ShieldCheck className="h-9 w-9 text-blue-500 group-hover:rotate-6 transition-transform duration-300" />
          <span className="text-2xl font-bold tracking-tight text-white">
            GovAssist <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">AI</span>
          </span>
        </Link>
        <h2 className="mt-6 text-center text-3xl font-extrabold tracking-tight text-slate-100">
          Create a new account
        </h2>
        <p className="mt-2 text-center text-sm text-slate-400">
          Or{" "}
          <Link href="/login" className="font-medium text-blue-400 hover:text-blue-300 transition-colors">
            sign in to your existing account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 px-4 sm:px-0">
        <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          {errorMsg && (
            <div className="mb-4 bg-red-950/30 border border-red-800/50 text-red-400 p-3 rounded-lg text-sm text-center">
              {errorMsg}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-slate-300">
                Full Name
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="h-5 w-5" />
                </div>
                <input
                  id="full_name"
                  type="text"
                  {...register("full_name")}
                  className="bg-slate-950/60 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 block w-full pl-10 pr-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none transition-colors"
                  placeholder="John Doe"
                />
              </div>
              {errors.full_name && (
                <p className="mt-1 text-xs text-red-400">{errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                Email address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="h-5 w-5" />
                </div>
                <input
                  id="email"
                  type="email"
                  {...register("email")}
                  className="bg-slate-950/60 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 block w-full pl-10 pr-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none transition-colors"
                  placeholder="name@example.com"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="h-5 w-5" />
                </div>
                <input
                  id="password"
                  type="password"
                  {...register("password")}
                  className="bg-slate-950/60 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 block w-full pl-10 pr-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none transition-colors"
                  placeholder="••••••••"
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300">
                Confirm Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="h-5 w-5" />
                </div>
                <input
                  id="confirmPassword"
                  type="password"
                  {...register("confirmPassword")}
                  className="bg-slate-950/60 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 block w-full pl-10 pr-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none transition-colors"
                  placeholder="••••••••"
                />
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400">{errors.confirmPassword.message}</p>
              )}
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-55 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-lg shadow-blue-600/20"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin h-5 w-5" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Register
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

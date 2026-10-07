"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAppStore } from "../../store/useAppStore";
import { api } from "../../services/api";
import { X, ShieldAlert, CheckCircle, Loader2 } from "lucide-react";

const eligibilitySchema = z.object({
  age: z.coerce.number().min(1, "Age must be at least 1").max(120, "Invalid age"),
  gender: z.string().min(1, "Required"),
  state: z.string().min(1, "Required"),
  occupation: z.string().min(1, "Required"),
  income: z.coerce.number().min(0, "Income must be positive"),
  category: z.string().min(1, "Required"),
  education: z.string().min(1, "Required"),
  disability: z.boolean().default(false),
  farmer: z.boolean().default(false),
  student: z.boolean().default(false),
  business: z.boolean().default(false),
  veteran: z.boolean().default(false),
  widow: z.boolean().default(false),
  minority: z.boolean().default(false),
});

type EligibilityFields = z.infer<typeof eligibilitySchema>;

const STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
  "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
  "West Bengal", "Delhi", "Puducherry"
];

const OCCUPATIONS = [
  "Farmer", "Student", "Unemployed", "Salaried Employee", "Self-employed", "Business Owner", "Other"
];

export default function EligibilityForm() {
  const { 
    isEligibilityModalOpen, 
    setEligibilityModalOpen, 
    setEligibilityProfile, 
    setEligibilityResults 
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(eligibilitySchema),
    defaultValues: {
      age: 25,
      gender: "Male",
      state: "Tamil Nadu",
      occupation: "Farmer",
      income: 180000,
      category: "General",
      education: "Secondary",
      disability: false,
      farmer: true,
      student: false,
      business: false,
      veteran: false,
      widow: false,
      minority: false,
    }
  });

  // Watch farmer/student to keep switches synchronized with occupation
  const watchOccupation = watch("occupation");

  React.useEffect(() => {
    if (watchOccupation === "Farmer") {
      setValue("farmer", true);
      setValue("student", false);
    } else if (watchOccupation === "Student") {
      setValue("student", true);
      setValue("farmer", false);
    } else if (watchOccupation === "Business Owner") {
      setValue("business", true);
      setValue("farmer", false);
      setValue("student", false);
    }
  }, [watchOccupation, setValue]);

  if (!isEligibilityModalOpen) return null;

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await api.post("/eligibility/check", data);
      setEligibilityProfile(data);
      setEligibilityResults(response.data);
      setEligibilityModalOpen(false);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err.response?.data?.detail || "Eligibility check failed. Please check inputs."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="flex justify-between items-center border-b border-slate-800 p-5 sticky top-0 bg-slate-900 z-10">
          <div>
            <h3 className="text-lg font-bold text-white">Smart Eligibility Profiler</h3>
            <p className="text-xs text-slate-400">Specify details to find matching government benefits</p>
          </div>
          <button
            onClick={() => setEligibilityModalOpen(false)}
            className="p-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form body */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6 flex-grow">
          {errorMsg && (
            <div className="bg-red-950/30 border border-red-800/50 text-red-400 p-3 rounded-lg text-xs text-center flex items-center justify-center gap-1.5">
              <ShieldAlert className="h-4 w-4" />
              {errorMsg}
            </div>
          )}

          {/* Demographic inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Age (Years)</label>
              <input
                type="number"
                {...register("age")}
                className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500"
              />
              {errors.age && <p className="mt-1 text-xs text-red-400">{errors.age.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Gender</label>
              <select
                {...register("gender")}
                className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Transgender">Transgender</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">State of Residence</label>
              <select
                {...register("state")}
                className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-blue-500"
              >
                {STATES.map((state) => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Primary Occupation</label>
              <select
                {...register("occupation")}
                className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-blue-500"
              >
                {OCCUPATIONS.map((occ) => (
                  <option key={occ} value={occ}>{occ}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Annual Family Income (INR)</label>
              <input
                type="number"
                {...register("income")}
                className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500"
              />
              {errors.income && <p className="mt-1 text-xs text-red-400">{errors.income.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Category</label>
                <select
                  {...register("category")}
                  className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="General">General</option>
                  <option value="OBC">OBC</option>
                  <option value="SC">SC</option>
                  <option value="ST">ST</option>
                  <option value="EWS">EWS</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Education</label>
                <select
                  {...register("education")}
                  className="bg-slate-950 border border-slate-800 block w-full px-3 py-2 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="None">None</option>
                  <option value="Primary">Primary</option>
                  <option value="Secondary">Secondary</option>
                  <option value="Higher Secondary">Higher Secondary</option>
                  <option value="Graduate">Graduate</option>
                  <option value="Post Graduate">Post Graduate</option>
                </select>
              </div>
            </div>
          </div>

          {/* Conditional Attributes (Switches) */}
          <div className="border-t border-slate-800/60 pt-5">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Welfare Criteria Qualifications</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("farmer")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Farmer</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("student")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Student</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("business")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Business / MSME</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("disability")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Disabled</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("veteran")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Military Veteran</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("widow")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Widow</span>
              </label>

              <label className="flex items-center gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 cursor-pointer hover:bg-slate-950 transition-colors">
                <input type="checkbox" {...register("minority")} className="rounded text-blue-600 focus:ring-blue-500" />
                <span className="text-xs text-slate-300 font-medium">Minority Group</span>
              </label>
            </div>
          </div>

          {/* Action triggers */}
          <div className="border-t border-slate-800/60 pt-5 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setEligibilityModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white rounded-lg text-sm font-semibold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-lg shadow-blue-600/15"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing Profile...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Evaluate Schemes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

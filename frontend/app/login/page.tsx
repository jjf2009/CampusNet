"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";

// Prototype UI only. This form never sends credentials anywhere — it exists
// to illustrate the student experience. Real authentication happens via
// 802.1X / RADIUS, not a web form, and no institutional password is ever
// entered here.

export default function StudentLogin() {
  const [submitted, setSubmitted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true); // purely local; nothing is transmitted or stored
  }

  return (
    <main className="min-h-screen bg-[#f6f8f9] text-slate-900">
      <div className="mx-auto grid min-h-screen max-w-7xl lg:grid-cols-[1.05fr_.95fr]">
        <section className="relative hidden overflow-hidden bg-[#123f5a] px-12 py-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -right-28 -top-28 h-80 w-80 rounded-full border-[40px] border-white/5" />
          <div className="relative">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white p-1.5">
                <Image
                  src="/gec_logo.jpg"
                  alt="Goa College of Engineering logo"
                  width={246}
                  height={205}
                  className="h-full w-full object-contain"
                />
              </div>
              <div>
                <p className="font-bold">Goa College of Engineering</p>
                <p className="text-[10px] uppercase tracking-[.2em] text-slate-300">
                  CampusNet access
                </p>
              </div>
            </div>
            <div className="mt-36 max-w-md">
              <p className="mb-5 text-xs font-bold uppercase tracking-[.2em] text-[#a8e0d5]">
                Secure campus connectivity
              </p>
              <h1 className="text-5xl font-bold leading-tight tracking-tight">
                Connect to your campus network.
              </h1>
              <p className="mt-6 max-w-sm text-sm leading-6 text-slate-300">
                Use your approved student account to access the college wireless
                network and online resources.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Protected by CampusNet authentication services
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-10 sm:px-10">
          <div className="w-full max-w-md">
            <div className="mb-10 flex items-center gap-3 lg:hidden">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white p-1.5 shadow-sm">
                <Image
                  src="/gec_logo.jpg"
                  alt="Goa College of Engineering logo"
                  width={246}
                  height={205}
                  className="h-full w-full object-contain"
                />
              </div>
              <div>
                <p className="font-bold">Goa College of Engineering</p>
                <p className="text-[10px] uppercase tracking-[.2em] text-slate-400">
                  CampusNet access
                </p>
              </div>
            </div>
            <div className="mb-8">
              <p className="text-xs font-bold uppercase tracking-[.18em] text-[#16736d]">
                Student portal
              </p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight">
                Sign in to Wi-Fi
              </h2>
              <p className="mt-3 text-sm leading-6 text-slate-500">
                Enter your college email and password to continue.
              </p>
            </div>

            {submitted && (
              <div
                role="status"
                className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800"
              >
                <b>Demo mode:</b> authentication is not connected. No credentials
                were sent or stored. Use fictional values only.
              </div>
            )}

            <form onSubmit={submit} className="space-y-5">
              <label className="block">
                <span className="mb-2 block text-xs font-bold">Student email</span>
                <input
                  required
                  type="email"
                  autoComplete="off"
                  placeholder="student01@gec.edu.in"
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none placeholder:text-slate-400 focus:border-[#16736d] focus:ring-4 focus:ring-[#16736d]/10"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs font-bold">Password</span>
                <div className="relative">
                  <input
                    required
                    type={showPassword ? "text" : "password"}
                    autoComplete="off"
                    placeholder="Enter demo password"
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 pr-20 text-sm outline-none placeholder:text-slate-400 focus:border-[#16736d] focus:ring-4 focus:ring-[#16736d]/10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </label>
              <button
                type="submit"
                className="w-full rounded-xl bg-[#16736d] px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-[#16736d]/20 hover:bg-[#125d59]"
              >
                Continue to network
              </button>
            </form>

            <div className="mt-8 border-t border-slate-200 pt-6 text-center">
              <p className="text-[11px] leading-5 text-slate-400">
                UI prototype only. Never enter a real institutional password in
                this demo.
              </p>
              <Link
                href="/"
                className="mt-4 inline-block text-xs font-bold text-[#16736d] hover:underline"
              >
                Open administrator dashboard →
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

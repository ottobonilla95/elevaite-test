"use client";
import type { SubmitHandler } from "react-hook-form";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import React from "react";
import { GoogleIcon } from "../icons/Google";

const formSchema = z
  .object({
    fullName: z.string().min(1, "Full Name is required"),
    email: z.string().email({ message: "Must be a valid Email" }).min(1, "Email is required"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    passwordConfirmation: z.string().min(1, "Password confirmation is required"),
  })
  .required()
  .refine((data) => data.password === data.passwordConfirmation, {
    path: ["passwordConfirmation"],
    message: "Password don't match",
  });
type FormValues = z.infer<typeof formSchema>;

export function SignUpForm(): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormValues>({ resolver: zodResolver(formSchema), mode: "onSubmit", reValidateMode: "onChange" });

  const onSubmit: SubmitHandler<FormValues> = (data) => {
    // eslint-disable-next-line no-console -- Temporary
    console.log(JSON.stringify(data));
    reset();
  };

  return (
    <div className="ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-3/5">
      <div className="ui-flex ui-flex-col ui-items-start ui-gap-5 ui-w-full">
        <form
          className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
          // eslint-disable-next-line @typescript-eslint/no-misused-promises -- This is meant to be like this.
          onSubmit={handleSubmit(onSubmit)}
        >
          {/* Full Name */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="fullName">
            Full Name
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.fullName ? "ui-border-red-500 ui-border" : ""
            }`}
            id="fullName"
            {...register("fullName")}
          />
          <p className="ui-text-sm ui-text-red-500">{errors.fullName?.message}</p>
          {/* Email */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="email">
            Email
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.email ? "ui-border-red-500 ui-border" : ""
            }`}
            id="email"
            {...register("email")}
          />
          <p className="ui-text-sm ui-text-red-500">{errors.email?.message}</p>
          {/* Password */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="password">
            Password
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.password ? "ui-border-red-500 ui-border" : ""
            }`}
            id="password"
            type="password"
            {...register("password")}
          />
          <p className="ui-text-sm ui-text-red-500">{errors.password?.message}</p>
          {/* Confirm Password */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="passwordConfirmation">
            Confirm Password
          </label>
          <input
            className={`ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg ${
              errors.passwordConfirmation ? "ui-border-red-500 ui-border" : ""
            }`}
            id="passwordConfirmation"
            type="password"
            {...register("passwordConfirmation")}
          />
          <p className="ui-text-sm ui-text-red-500">{errors.passwordConfirmation?.message}</p>
          {/* Submit */}
          <button className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg" type="submit">
            Next
          </button>
        </form>
        <span className="ui ui-font-medium ui-text-sm">
          By signing up, I agree to sessions,{" "}
          <Link className="ui ui-text-[#E75F33]" href="">
            Terms & Conditions
          </Link>
          {", "}
          <Link className="ui ui-text-[#E75F33]" href="">
            Privacy Policy
          </Link>{" "}
          and to receive sessions news and updates.
        </span>
      </div>
      <div className="ui-w-full ui-flex ui-flex-row ui-items-center ui-gap-4 ui-justify-center">
        <line className="ui-w-full ui-h-px ui-bg-slate-300" />
        or
        <line className="ui-w-full ui-h-px ui-bg-slate-300" />
      </div>
      <button
        className="ui-flex ui-flex-row ui-items-center ui-justify-center ui-gap-3 ui-py-3 ui-px-10 ui-bg-[#161616] ui-w-full ui-rounded-lg"
        type="submit"
      >
        <GoogleIcon />
        Sign Up With Google
      </button>
    </div>
  );
}

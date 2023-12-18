"use client";

import { useForm, type SubmitHandler } from "react-hook-form";
import React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { GoogleIcon } from "../icons/Google";

const formSchema = z
  .object({
    email: z.string().email({ message: "Must be a valid Email" }).min(1, "Email is required"),
    password: z.string().min(1, "Password is required"),
  })
  .required();
type FormValues = z.infer<typeof formSchema>;

export function LogInForm({
  authenticate,
}: {
  authenticate: (
    prevstate: string,
    formData: FormValues
  ) => Promise<"Invalid credentials." | "Something went wrong." | undefined>;
}): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
    resetField,
  } = useForm<FormValues>({ resolver: zodResolver(formSchema) });

  const onSubmit: SubmitHandler<FormValues> = async (data: FormValues) => {
    const res = await authenticate("", data);
    if (res) {
      setError("root.credentials", { message: res });
      resetField("password");
    } else {
      reset();
    }
  };

  return (
    <div className="ui-flex ui-flex-col ui-gap-[29px] ui-items-start ui-w-3/5">
      <div className="ui-flex ui-flex-col ui-items-start ui-gap-5 ui-w-full">
        <form
          className="ui-flex ui-flex-col ui-items-start ui-gap-3 ui-font-inter ui-w-full"
          // eslint-disable-next-line @typescript-eslint/no-misused-promises -- It's meant to be like this
          onSubmit={handleSubmit(onSubmit)}
        >
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
          <p className="ui-text-sm ui-text-red-500">{errors.root?.credentials?.message}</p>
          {/* Submit */}
          <button className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg" type="submit">
            Next
          </button>
        </form>
      </div>
      <button
        className="ui-flex ui-flex-row ui-items-center ui-justify-center ui-gap-3 ui-py-3 ui-px-10 ui-bg-[#161616] ui-w-full ui-rounded-lg"
        type="submit"
      >
        <GoogleIcon />
        Sign In With Google
      </button>
    </div>
  );
}

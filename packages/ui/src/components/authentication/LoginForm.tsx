import type { SubmitHandler } from "react-hook-form";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";

const formSchema = yup
  .object({
    email: yup.string().email().required("Email is required"),
    password: yup.string().required("Password is required"),
  })
  .required();
type FormValues = yup.InferType<typeof formSchema>;

export function LogInForm(): JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormValues>({ resolver: yupResolver(formSchema), mode: "onSubmit", reValidateMode: "onChange" });

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
          onSubmit={() => handleSubmit(onSubmit)}
        >
          {/* Email */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="email">
            Email
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="email"
            {...register("email")}
          />
          <p>{errors.email?.message}</p>
          {/* Password */}
          <label className="ui-text-lg ui-font-semibold ui-font-source_sans" htmlFor="password">
            Password
          </label>
          <input
            className="ui-py-[13px] ui-px-5 ui-bg-[#161616] ui-w-full ui-rounded-lg"
            id="password"
            type="password"
            {...register("password")}
          />
          <p>{errors.password?.message}</p>
          {/* Submit */}
          <button className="ui-py-3 ui-px-10 ui-bg-orange-500 ui-rounded-lg" type="submit">
            Next
          </button>
        </form>
      </div>
    </div>
  );
}

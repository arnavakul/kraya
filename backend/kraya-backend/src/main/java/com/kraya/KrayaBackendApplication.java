package com.kraya;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableFeignClients
public class KrayaBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(KrayaBackendApplication.class, args);
	}

}
